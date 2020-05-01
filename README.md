A collection of scripts providing a basic GPU monitoring by retrieving metrics from nvidia-smi and sending those metrics to Cloudwatch.
- gpumon.py: the gpu monitoring script itself
- gpumon.service: the systemd service file helps to provide a stable way to run this script on the background. 
- gpu-alarms.tg: Terraform file consists of definitions creating autoscaling policies/cloudwatch alarms based on the custom metrics provided by the gpumon.py script. .tf file will require proper variables set unique in each use-case and basically was a part of the module creating EKS worker nodes with ASG, launch configurations, etc. 
