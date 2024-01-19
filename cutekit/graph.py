import os

from typing import Optional, cast

from . import vt100, cli, model


def view(
    registry: model.Registry,
    target: model.Target,
    scope: Optional[str] = None,
    showExe: bool = True,
    showDisabled: bool = False,
):
    from graphviz import Digraph  # type: ignore

    g = Digraph(target.id, filename="graph.gv")

    g.attr("graph", splines="ortho", rankdir="BT", ranksep="1.5")
    g.attr("node", shape="ellipse")
    g.attr(
        "graph",
        label=f"<<B>{scope or 'Full Dependency Graph'}</B><BR/>{target.id}>",
        labelloc="t",
    )

    scopeInstance = None

    if scope is not None:
        scopeInstance = registry.lookup(scope, model.Component)

    for component in registry.iterEnabled(target):
        if not component.type == model.Kind.LIB and not showExe:
            continue

        if (
            scopeInstance is not None
            and component.id != scope
            and component.id not in scopeInstance.resolved[target.id].required
        ):
            continue

        if component.resolved[target.id].enabled:
            fillcolor = "lightgrey" if component.type == model.Kind.LIB else "lightblue"
            shape = "plaintext" if not scope == component.id else "box"

            g.node(
                component.id,
                f"<<B>{component.id}</B><BR/>{vt100.wordwrap(component.description, 40,newline='<BR/>')}>",
                shape=shape,
                style="filled",
                fillcolor=fillcolor,
            )

            for req in component.requires:
                g.edge(component.id, req)

            for req in component.provides:
                isChosen = target.routing.get(req, None) == component.id

                g.edge(
                    req,
                    component.id,
                    arrowhead="none",
                    color=("blue" if isChosen else "black"),
                )
        elif showDisabled:
            g.node(
                component.id,
                f"<<B>{component.id}</B><BR/>{vt100.wordwrap(component.description, 40,newline='<BR/>')}<BR/><BR/><I>{vt100.wordwrap(str(component.resolved[target.id].reason), 40,newline='<BR/>')}</I>>",
                shape="plaintext",
                style="filled",
                fontcolor="#999999",
                fillcolor="#eeeeee",
            )

            for req in component.requires:
                g.edge(component.id, req, color="#aaaaaa")

            for req in component.provides:
                g.edge(req, component.id, arrowhead="none", color="#aaaaaa")

    g.view(filename=os.path.join(target.builddir, "graph.gv"))


class GraphCmd:
    mixins: cli.Arg[str] = cli.Arg("m", "mixins", "Mixins to apply", default="")
    scope: cli.Arg[str] = cli.Arg("s", "scope", "Scope to show", default="")
    onlyLibs: cli.Arg[bool] = cli.Arg("l", "only-libs", "Only show libraries", default=False)
    showDisabled: cli.Arg[bool] = cli.Arg("d", "show-disabled", "Show disabled components", default=False)

@cli.command("g", "graph", "Show the dependency graph")
def _(args: GraphCmd):
    registry = model.Registry.use(args)
    target = model.Target.use(args)

    view(registry, target, scope=args.scope, showExe=not args.onlyLibs, showDisabled=args.showDisabled)
