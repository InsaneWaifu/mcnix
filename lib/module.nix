{ self }:
{ config, lib, pkgs, ... }:
let cfg = config.mcnix;
sync =
  pkgs.python3.pkgs.buildPythonApplication {
    pname = "sync-plugins";
    version = "0.1.0";

    src = ./../tool;

    format = "other";

    installPhase = ''
      mkdir -p $out/bin
      install -m755 tool.py $out/bin/sync-plugins
    '';

    meta = with pkgs.lib; {
      description = "Sync Minecraft plugins from schema diff";
      license = licenses.mit;
      platforms = platforms.linux;
    };
  };
in {
  options.mcnix.enable = lib.mkEnableOption "Enable minecraft";
  options.mcnix.servers = lib.mkOption {
    type = types.addCheck (types.attrsOf types.package) (x: x != {});
    default = {};
    description = "Named minecraft server configs";
  };
  config = mkIf cfg.enable {
    systemd.services = lib.mapAttrs'
      (name: value: {
        name = "mcnix-${name}";
        value = {
          description = "mcnix server ${name}";
          wantedBy = [ "multi-user.target" ];
          after = [ "network.target" ];
          wants = [ "network.target" ];
          serviceConfig = {
            ExecStartPre = "${lib.getExe sync} --current-schema /var/lib/mcnix/${name}/schema --new-schema ${value} --plugins-dir /var/lib/mcnix/${name}/plugins";
            ExecStart = "${value.java} ${value.javaFlags} -jar ${value.serverJar}";
            DynamicUser = true;
            PrivateTmp = true;
            NoNewPrivileges = true;
            StateDirectory = "mcnix/${name}";
            RuntimeDirectory = "mcnix/${name}";
            CacheDirectory = "mcnix/${name}";
            LogsDirectory = "mcnix/${name}";
            Restart = "always";
            RestartSec = "5s";
            StartLimitIntervalSec = 60;
            StartLimitBurst = 10;
            ProtectSystem = "strict";
            ProtectHome = true;
            RestrictSUIDSGID = true;
            LockPersonality = true;
          };
        };
      }) cfg.servers;
  };
}

