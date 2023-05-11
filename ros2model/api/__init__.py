import re
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ament_index_python import get_package_share_directory
from jinja2 import Environment, FileSystemLoader
from rcl_interfaces.msg import ParameterType
from ros2node.api import TopicInfo


@dataclass
class Message:
    name: str
    message: dict


@dataclass
class Service:
    name: str
    request: dict
    response: dict


@dataclass
class Action:
    name: str
    goal: dict
    result: dict
    feedback: dict


def get_spec_files(path: Path, glob: str) -> list:
    """Get all the spec files in a directory.

    Args:
        path (Path): Path to the directory containing the spec files.
        glob (str): Glob pattern to match the spec files.

    Returns:
        list: List of spec files.
    """
    return [f for f in path.glob(glob) if f.is_file()]


def prepare_output_dir(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)


def split_line(line: str):
    """Split a line into a tuple of type and name.

    Args:
        line (str): The line to split.

    Returns:
        tuple: The type and name of the line.
    """
    line = line.replace("\n", "")
    if line.startswith("#") or "=" in line or len(line) == 0 or line.isspace():
        return None, None
    if "#" in line:
        line = line.split("#")[0]
    if line.isspace():
        return None, None
    line = re.sub(r"\[.*\]", "[]", line)
    split = line.split(maxsplit=1)

    split[0] = split[0].replace("/", ".")

    return split[0].strip(), split[1].strip()


def process_msg_file(msg_file: Path):
    """Process a message file."""
    name = msg_file.stem
    message = {}
    file = msg_file.open()
    for line in file:
        if "=" in line:
            continue
        line = line.replace("\n", "")
        if len(line) == 0:
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        res = any(ele.isupper() for ele in typename)
        if res:
            typename = '"' + typename + '"'
            typename = typename.replace("[]", "") + "[]"
        message[variablename] = typename
    file.close()
    return name, message


def process_srv_file(srv_file: Path):
    """Process a message file."""
    name = srv_file.stem
    request = {}
    response = {}
    file = srv_file.open()
    resp = False
    for line in file:
        if "---" in line:
            resp = True
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        res = any(ele.isupper() for ele in typename)
        if res:
            typename = '"' + typename + '"'
            typename = typename.replace("[]", "") + "[]"
        if resp:
            response[variablename] = typename
        else:
            request[variablename] = typename
    file.close()
    return name, request, response


def process_action_file(action_file: Path):
    """Process an aciton file."""
    name = action_file.stem
    goal = {}
    result = {}
    feedback = {}
    file = action_file.open()
    border = 0
    for line in file:
        if "---" in line:
            border += 1
            continue
        typename, variablename = split_line(line)
        if typename is None:
            continue
        if variablename is None:
            continue
        res = any(ele.isupper() for ele in typename)
        if res:
            typename = '"' + typename + '"'
            typename = typename.replace("[]", "") + "[]"
        if border == 0:
            goal[variablename] = typename
        if border == 1:
            result[variablename] = typename
        if border == 2:
            feedback[variablename] = typename
    file.close()
    return name, goal, result, feedback


def process_msg_dir(msg_path: Path):
    msg_files = get_spec_files(msg_path, "*.msg")
    msgs = []
    for msg_file in msg_files:
        name, message = process_msg_file(msg_file)
        msg = Message(name, message)
        msgs.append(msg)
    return msgs


def process_srv_dir(msg_path: Path):
    srv_files = get_spec_files(msg_path, "*.srv")
    srvs = []
    for srv_file in srv_files:
        name, request, response = process_srv_file(srv_file)
        srv = Service(name, request, response)
        srvs.append(srv)
    return srvs


def process_action_dir(msg_path: Path):
    action_files = get_spec_files(msg_path, "*.action")
    actions = []
    for action_file in action_files:
        name, goal, result, feedback = process_action_file(action_file)
        action = Action(name, goal, result, feedback)
        actions.append(action)
    return actions


def fix_topic_types(node_name: str, topics: Iterable[TopicInfo]):
    for topic in topics:
        if "/" not in topic.types[0]:
            topic.types[0] = '"' + topic.types[0] + '"'
        topic.types[0] = topic.types[0].replace("/msg/", ".")
        topic.types[0] = topic.types[0].replace("/srv/", ".")
        topic.types[0] = topic.types[0].replace("/action/", ".")
        # topic.name = topic.name.replace("node_name", "")
        # topic.name = topic.name.replace("/", "")


def fix_topic_names(node_name: str, topics: Iterable[TopicInfo]) -> Iterable[TopicInfo]:
    new_topics = []
    for topic in topics:
        if not node_name.startswith("/"):
            node_name = "/node_name"
        name = topic.name.replace(node_name, "~")
        # name = name.replace("/", "")
        new_topics.append(TopicInfo(name, topic.types))
    return new_topics


def get_parameter_type_string(parameter_type):
    mapping = {
        ParameterType.PARAMETER_BOOL: "Boolean",
        ParameterType.PARAMETER_INTEGER: "Integer",
        ParameterType.PARAMETER_DOUBLE: "Double",
        ParameterType.PARAMETER_STRING: "String",
        ParameterType.PARAMETER_BYTE_ARRAY: "Array: Byte",
        ParameterType.PARAMETER_BOOL_ARRAY: "Array: Boolean",
        ParameterType.PARAMETER_INTEGER_ARRAY: "Array: Integer",
        ParameterType.PARAMETER_DOUBLE_ARRAY: "Array: Double",
        ParameterType.PARAMETER_STRING_ARRAY: "Array: String",
        ParameterType.PARAMETER_NOT_SET: "Any",
    }
    return mapping[parameter_type]
