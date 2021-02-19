create table user
(
    mobile                bigint unsigned primary key,
    passwd                varchar(64),
    nickname              varchar(32),
    sex                   enum ('male', 'female'),
    portrait              char(36) references resource (uuid),
    default_location      point srid 4326,
    default_location_name varchar(64),
    mark                  set ('test') comment '特殊标记：用来给用户增加一系列状态',
    create_at             timestamp not null default current_timestamp
);

# 用户登录令牌
create table token
(
    user     bigint unsigned,
    appid    char(32),
    hex      char(32),
    # privilege set (''),
    deadline timestamp,
    primary key (user, appid),
    foreign key (user) references user (mobile),
    index (deadline)
);

# 每个小时清理一次过期token
create event token_event_auto_clear on schedule every 1 hour do delete
                                                                from token
                                                                where deadline < current_timestamp;

create table resource
(
    uuid      char(36) primary key,
#     visibility enum ('public', '') default 'public', # 可见性
    from_user bigint unsigned not null,
    create_at timestamp       not null default current_timestamp,
    foreign key (from_user) references user (mobile)
);

alter table user
    add foreign key (portrait) references resource (uuid);

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

create table commodity
(
    id            int unsigned primary key auto_increment,
    name          varchar(32)             not null,
    detail        text,
    from_user     bigint unsigned,
    location      point srid 4326         not null comment 'null = point(0, 90)',
    location_name varchar(64),
    on_offer      bool                    not null default false,
    price         decimal(16, 2) unsigned not null,
    sales_volume  int unsigned            not null default 0,
    photo         char(36),
    foreign key (photo) references resource (uuid)
);

create table `order`
(
    id               int unsigned primary key auto_increment,
    from_user        bigint unsigned           not null,
    destination      point srid 4326           not null comment '交付地点，null = point(0, 90)',
    destination_name varchar(64),
    emergency_level  enum ('normal', 'urgent') not null default 'normal',
    create_at        timestamp                 not null default current_timestamp,
    receive_at       timestamp,
    executor         bigint unsigned,
    close_at         timestamp,
    close_state      enum ('finish', 'cancel'),
    foreign key (from_user) references user (mobile),
    foreign key (executor) references user (mobile),
    spatial key (destination),
    constraint order_chk_receive check ((receive_at is null and executor is null) or
                                        (receive_at is not null and executor is not null)),
    constraint order_chk_close check ((close_at is null and close_state is null) or
                                      (close_at is not null and close_state is not null))
);

create table task
(
    id               int unsigned primary key auto_increment,
    name             varchar(32)             not null,
    type             varchar(32)             not null,
    category         varchar(32),
    detail           text,
    protected_info   text,
    photo            char(36),
    `order`          int unsigned            not null,
    destination      point srid 4326         not null comment '任务地点，null = point(0, 90)',
    destination_name varchar(64),
    count            int unsigned            not null comment '需要物品的数量',
    reward           decimal(16, 2) unsigned not null,
    in_at            timestamp,
    out_at           timestamp,
    foreign key (photo) references resource (uuid),
    foreign key (`order`) references `order` (id),
    spatial key (destination)
);
