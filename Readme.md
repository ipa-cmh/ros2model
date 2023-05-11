# ROS Model integation into ROS2 Command

### Creates a .ros file for the interface package.
```
ros2 model interface_package [-o Outputfile] <package-name>
```

```
ros2 model interface_package -a -o <folder-name>
```

### Creates a partial .ros2 file for the running node, only the node specific part, need to update "artifact" manually. The node must be running.
```
ros2 model running_node [-o Outputfile] <node-name>
```

### Creates partial .ros2 fils for the running system, only the node specific part, need to update "artifact" manually. The node must be running.
```
ros2 model running_node -ga -dir <folder-name>
```
