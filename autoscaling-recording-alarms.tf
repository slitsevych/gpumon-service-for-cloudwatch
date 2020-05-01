####################################################################
########### ASG Autoscaling resources: policies ####################
####################################################################
resource "aws_autoscaling_policy" "eks-gpu-simple-autoscaling-up" {
  count                  = "${var.node_type == "gpu" ? 1 : 0}"
  name                   = "autoscaling-up-${var.env_name}"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.eks-autoscaling-group-gpu.name}"

}

resource "aws_autoscaling_policy" "eks-gpu-simple-autoscaling-down" {
  count                  = "${var.node_type == "gpu" ? 1 : 0}"
  name                   = "autoscaling-down-${var.env_name}"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.eks-autoscaling-group-gpu.name}"

}

######################################################################
###########  Cloudwatch alarms required for Autoscaling  #############
# ####################################################################
data "aws_instances" "asg-instances" {
  instance_tags = {
        Name = "eks-gpu-${var.env_name}"
  }
  instance_state_names = ["running"]
}

resource "aws_cloudwatch_metric_alarm" "gpu-usage-alarm-up" {
  count               = "${var.node_type == "gpu" ? 1 : 0}"
  alarm_name          = "gpu-usage-alarm-up-${var.env_name}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "GPUUsage"
  namespace           = "GPUMonitoring"
  period              = "180"
  statistic           = "Average"
  threshold           = "75"
  treat_missing_data  = "missing"
  datapoints_to_alarm = 2
  alarm_actions       = ["${aws_sns_topic.cloudwatch-autoscaling-alarm.arn}"]
  ok_actions          = ["${aws_sns_topic.cloudwatch-autoscaling-alarm.arn}"]

  dimensions {
    InstanceId         = "${data.aws_instances.asg-instances.ids[count.index]}"
    GPUNumber          = 0
  }

  alarm_description = "This metric monitors EKS-gpu-node instance GPU utilization"
  alarm_actions     = ["${aws_autoscaling_policy.eks-gpu-simple-autoscaling-up.arn}"]
}

resource "aws_cloudwatch_metric_alarm" "gpu-usage-alarm-down" {
  count               = "${var.node_type == "gpu" ? 1 : 0}"
  alarm_name          = "gpu-usage-alarm-down-${var.env_name}"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "GPUUsage"
  namespace           = "GPUMonitoring"
  period              = "180"
  statistic           = "Average"
  threshold           = "25"
  treat_missing_data  = "missing"
  datapoints_to_alarm  = 2
  alarm_actions       = ["${aws_sns_topic.cloudwatch-autoscaling-alarm.arn}"]
  ok_actions          = ["${aws_sns_topic.cloudwatch-autoscaling-alarm.arn}"]

  dimensions {
    InstanceId         = "${data.aws_instances.asg-instances.ids[count.index]}"
    GPUNumber          = 0
  }

  alarm_description = "This metric monitors EKS-gpu-node instance GPU utilization"
  alarm_actions     = ["${aws_autoscaling_policy.eks-gpu-simple-autoscaling-down.arn}"]
}

resource "aws_sns_topic" "eks-gpu-cloudwatch-autoscaling-alarm" {
  count  = "${var.node_type == "gpu" ? 1 : 0}"
  name   = "cloudwatch-autoscaling-alarm-${var.env_name}"

  provisioner "local-exec" {
    command = "aws sns subscribe --topic-arn ${self.arn} --protocol email --notification-endpoint ${var.email}"
  }
}