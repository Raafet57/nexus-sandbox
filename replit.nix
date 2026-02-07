{ pkgs }: {
  deps = [
    pkgs.nodejs_20
    pkgs.python312
    pkgs.postgresql_16
    pkgs.redis
  ];
}
