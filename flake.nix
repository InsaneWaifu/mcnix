{
  description = "Minecraft server framework";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      lib = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        import ./lib { inherit pkgs self; }
      );

      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          fetch-plugin = pkgs.writers.writePython3Bin "fetch-plugin" {
            libraries = [ pkgs.python3Packages.rich ];
          } (builtins.readFile ./searcher/search.py);
        }
      );
      apps = forAllSystems (system: {
        fetch-plugin = {
          type = "app";
          program = "${self.packages.${system}.fetch-plugin}/bin/fetch-plugin";
        };
      });

      formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-tree);

      nixosModules.default = import ./lib/module.nix { inherit self; };
    };
}
