{
  description = "EPG processing environment";
  
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  
  outputs = { self, nixpkgs }: {
    devShells.x86_64-linux.default = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      buildInputs = [
        nixpkgs.legacyPackages.x86_64-linux.python3
        nixpkgs.legacyPackages.x86_64-linux.curl
        nixpkgs.legacyPackages.x86_64-linux.git
      ];
      
      shellHook = ''
        echo "Nix development environment ready"
      '';
    };
  };
}
