source install/local_setup.bash

ros2 run health service

```
ros2 service call /health_check std_srvs/srv/Trigger
requester: making request: std_srvs.srv.Trigger_Request()

response:
std_srvs.srv.Trigger_Response(success=True, message='Everything looking ok over here!')
```