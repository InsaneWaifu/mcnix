{ pkgs, self }:

let
  inherit (pkgs) lib;
  validateArtifact =
    plugin:
    (
      assert builtins.isAttrs plugin;
      assert lib.isDerivation plugin.jar;
      assert builtins.isString plugin.jarName;
      plugin
    );

in
{
  mkServer =
    {
      java,
      serverJar,
      javaFlags,
      plugins ? [ ],
    }:
    pkgs.writeTextFile {
      name = "server-manifest.json";
      text = builtins.toJSON {
        serverJar = validateArtifact serverJar;
        plugins = builtins.map validateArtifact plugins;
        inherit javaFlags;
      };
      passthru = {
        java = lib.getExe java;
        serverJar = serverJar.jar;
        inherit javaFlags;
      };
    };

  fetchHangarPlugin = slug: version: hash: {
    jar = pkgs.fetchurl {
      url = "https://hangar.papermc.io/api/v1/projects/${slug}/versions/${version}/PAPER/download";
      pname = slug;
      inherit version hash;
    };
    jarName = "${slug}-${version}";
  };

  fetchSpigotPlugin = name: pluginId: versionId: hash: {
    jar = pkgs.fetchurl {
      url = "https://api.spiget.org/v2/resources/${pluginId}/versions/${versionId}/download/proxy";
      inherit hash name;
    };
    jarName = "${name}-${versionId}";
  };

  fetchPlugin = name: url: hash: {
      jar = pkgs.fetchurl {
          inherit url name hash;
      };
      jarName = "${name}";
  };

  fetchPaperJar =
    {
      version,
      build,
      worker_url ? "https://jsonpath-worker.insanewaifu.workers.dev",
      hash,
    }:
    let
      metadataUrl = "https://fill.papermc.io/v3/projects/paper/versions/${version}/builds/${build}";
      downloadPath = "$.downloads[\"server:default\"].url";
    in
    {
      jar = pkgs.fetchurl {
        url = "${worker_url}?url=${pkgs.lib.strings.escapeURL metadataUrl}&path=${pkgs.lib.strings.escapeURL downloadPath}";
        pname = "paper";
        version = "${version}-${build}";
        inherit hash;
      };
      jarName = "paper-${version}-${build}";
    };
}
