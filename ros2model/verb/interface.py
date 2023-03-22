from pathlib import Path

from ament_index_python import get_package_share_directory
from jinja2 import Environment, FileSystemLoader
from ros2cli.node.strategy import add_arguments
from ros2interface.api import get_interface_packages

from ros2model.api import process_action_dir, process_msg_dir, process_srv_dir
from ros2model.verb import VerbExtension


class InterfacePackageVerb(VerbExtension):
    """Output information about a node."""

    def add_arguments(self, parser, cli_name):
        add_arguments(parser)
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            "-i",
            "--interface_package_name",
            help="Name of the package containing the interface",
        )
        group.add_argument(
            "-a",
            "--all",
            action="store_true",
            help="Generate all message in the workspace",
        )

        parser.add_argument(
            "-o",
            "--output",
            default=".",
            help="The output file for the generated model.",
        )

    def gen(self, interface_package_name, output_file):
        package_share_path = get_package_share_directory(
            interface_package_name)
        msg_path = Path(package_share_path) / "msg"
        srv_path = Path(package_share_path) / "srv"
        actions_path = Path(package_share_path) / "action"
        msgs = process_msg_dir(msg_path)
        srvs = process_srv_dir(srv_path)
        actions = process_action_dir(actions_path)
        print(
            "Found {} messages, {} services and {} actions.".format(
                len(msgs), len(srvs), len(actions)
            )
        )
        env = Environment(
            loader=FileSystemLoader(
                get_package_share_directory("ros2model") + "/templates"
            ),
            autoescape=False,
        )
        template = env.get_template("model.jinja")
        contents = template.render(
            package_name=interface_package_name,
            msgs=msgs,
            srvs=srvs,
            actions=actions,
        )
        output_file = Path(output_file)
        output_file.parents[0].mkdir(parents=True, exist_ok=True)
        print("Writing model to {}".format(output_file.absolute()))
        output_file.touch()
        output_file.write_bytes(contents.encode("utf-8"))

    def main(self, *, args):
        if args.all:
            interface_pkgs = get_interface_packages()
            for pkg in interface_pkgs:
                self.gen(pkg, f"{args.output}/{pkg}.ros")
        else:
            self.gen(args.interface_package_name,
                     f"{args.interface_package_name}.ros")
