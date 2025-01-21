from pathlib import Path
from . import cli, model, builder, shell
import os


class PackageArgs(model.TargetArgs):
    prefix: str = cli.arg(None, "prefix", "Installation prefix")
    layout: str = cli.arg(None, "layout", "Installation layout")


class InstallPackageArgs(PackageArgs):
    sysroot: str = cli.arg(None, "sysroot", "System root directory", "/")


def install(args: InstallPackageArgs):
    args.prefix = args.prefix or "/"
    args.sysroot = os.path.abspath(args.sysroot or "/")

    args.props["prefix"] = args.prefix

    dest = Path(args.sysroot) / Path(args.prefix).relative_to("/")

    scope = builder.TargetScope.use(args)
    products = builder.build(scope, "all")

    print(f"Installing to {dest}...")
    print(f"sysroot: {args.sysroot}")
    print(f"prefix: {args.prefix}")

    print("")

    shell.mkdir(str(dest / "bin"))
    shell.mkdir(str(dest / "share"))
    for product in products:
        component = product.component
        print(f"Installing {component.id}...")
        if component.type == model.Kind.EXE:
            name = component.id
            name = name.removesuffix(".main").removesuffix(".cli")
            shell.cp(str(product.path), str(dest / "bin" / name))

        ressources = builder.listRes(component)
        if ressources:
            shell.mkdir(str(dest / "share" / component.id))
            for res in builder.listRes(component):
                rel = Path(res).relative_to(component.subpath("res"))
                resDest = dest / "share" / component.id / rel
                resDest.parent.mkdir(parents=True, exist_ok=True)
                shell.cp(str(res), str(resDest))


# MARK: Commands ---------------------------------------------------------------


@cli.command(None, "package", "Package the project")
def _(): ...


class BuildPackageArgs(PackageArgs):
    format: str = cli.arg(None, "format", "Package format")


@cli.command(None, "package/build", "Package the project")
def _(args: BuildPackageArgs):
    pass


@cli.command(None, "package/install", "Package the project")
def _(args: InstallPackageArgs):
    install(args)
