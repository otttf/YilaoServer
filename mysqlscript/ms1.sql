create table user
(
    mobile           bigint unsigned primary key,
    sha256_passwd    char(64),
    nickname         varchar(32),
    sex              enum ('male', 'female'),
    portrait         int unsigned references resource (id),
    default_location point,
    address          varchar(64),
    mark             set ('test') comment '特殊标记：用来给用户增加一系列状态',
    verify_at        timestamp,
    constraint user_chk_mobile check (mobile regexp '^1[3-9]\\d{9}$'),
    constraint user_chk_locate check (default_location != point(0, 90) or address is null)
);

# 用户登录令牌
create table token
(
    user     bigint unsigned,
    platform enum ('phone', 'browser', 'pc'),
    hex      char(32),
    primary key (user, platform),
    foreign key (user) references user (mobile)
);

create table resource
(
    id        int unsigned primary key auto_increment,
    suffix    varchar(16),
    data      mediumblob      not null,
    from_user bigint unsigned not null,
    create_at timestamp       not null default current_timestamp,
    delete_at timestamp,
    foreign key (from_user) references user (mobile),
    index (delete_at)
);

alter table user
    add foreign key (portrait) references resource (id);

create table dialog
(
    id        int unsigned primary key auto_increment,
    content   text      not null,
    from_user bigint unsigned,
    to_user   bigint unsigned,
    send_at   timestamp not null default current_timestamp,
    foreign key (from_user) references user (mobile),
    foreign key (to_user) references user (mobile)
);

create table dialog_resource_reference
(
    dialog   int unsigned,
    resource int unsigned,
    primary key (dialog, resource),
    foreign key (dialog) references dialog (id),
    foreign key (resource) references resource (id)
);

create table store
(
    id        int unsigned primary key auto_increment,
    name      varchar(32) not null,
    location  point       not null comment 'null = point(0, 90)',
    address   varchar(64),
    photo     int unsigned,
    from_user bigint unsigned,
    foreign key (photo) references resource (id),
    foreign key (from_user) references user (mobile),
    spatial key (location),
    constraint store_chk_locate check (location != point(0, 90) or address is null)
);

create table commodity
(
    id           int unsigned primary key auto_increment,
    name         varchar(32)             not null,
    store        int unsigned            not null,
    on_offer     bool                    not null default false,
    price        decimal(16, 2) unsigned not null,
    sales_volume int unsigned            not null default 0,
    photo        int unsigned,
    foreign key (store) references store (id),
    foreign key (photo) references resource (id)
);

create table `order`
(
    id              int unsigned primary key auto_increment,
    from_user       bigint unsigned           not null,
    destination     point                     not null comment '交付地点，null = point(0, 90)',
    address         varchar(64),
    emergency_level enum ('normal', 'urgent') not null default 'normal',
    create_at       timestamp                 not null default current_timestamp,
    receive_at      timestamp,
    executor        bigint unsigned,
    close_at        timestamp,
    close_state     enum ('finish', 'cancel'),
    foreign key (from_user) references user (mobile),
    foreign key (executor) references user (mobile),
    spatial key (destination),
    constraint order_chk_locate check (destination != point(0, 90) or address is null),
    constraint order_chk_receive check ((receive_at is null and executor is null) or
                                        (receive_at is not null and executor is not null)),
    constraint order_chk_close check ((receive_at is null and close_at is null) or
                                      (close_at is null and close_state is null) or
                                      (receive_at is not null and close_at is not null and close_state is not null))
);

create table task
(
    id             int unsigned primary key auto_increment,
    name           varchar(32)             not null,
    detail         text,
    protected_info text,
    photo          int unsigned,
    `order`        int unsigned            not null,
    tangible       bool                    not null,
    destination    point                   not null comment '任务地点，null = point(0, 90)',
    address        varchar(64),
    count          int unsigned            not null comment '需要物品的数量',
    reward         decimal(16, 2) unsigned not null,
    in_at          timestamp,
    out_at         timestamp,
    foreign key (photo) references resource (id),
    foreign key (`order`) references `order` (id),
    spatial key (destination),
    constraint task_chk_tangible check (tangible is not null or destination != point(0, 90)),
    constraint task_chk_locate check (destination != point(0, 90) or address is null)
);
