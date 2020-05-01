import urllib.request as urllib
import boto3
from pynvml import *
from datetime import datetime
from time import sleep

### CHOOSE REGION ####
EC2_REGION = 'us-east-1'

###CHOOSE NAMESPACE PARMETERS HERE###
my_NameSpace = 'GPUMonitoring' 

### CHOOSE PUSH INTERVAL ####
sleep_interval = 5

### CHOOSE STORAGE RESOLUTION (BETWEEN 1-60) ####
store_reso = 60

#Instance information
BASE_URL = 'http://169.254.169.254/latest/meta-data/'
INSTANCE_ID = urllib.urlopen(BASE_URL + 'instance-id').read().decode('utf-8')
INSTANCE_AZ = urllib.urlopen(BASE_URL + 'placement/availability-zone').read().decode('utf-8')
EC2_REGION = INSTANCE_AZ[:-1]

TIMESTAMP = datetime.now().strftime('%Y-%m-%dT%H')
TMP_FILE = '/tmp/GPU_TEMP'
TMP_FILE_SAVED = TMP_FILE + TIMESTAMP

# Create CloudWatch client
cloudwatch = boto3.client('cloudwatch', region_name=EC2_REGION)

# Flag to push to CloudWatch
PUSH_TO_CW = True


def getPowerDraw(handle):
    try:
        powDraw = nvmlDeviceGetPowerUsage(handle) / 1000.0
        powDrawStr = '%.2f' % powDraw
    except NVMLError as err:
        powDrawStr = handleError(err)
        PUSH_TO_CW = False
    return powDrawStr


def getTemp(handle):
    try:
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
    except NVMLError as err:
        temp = handleError(err) 
        PUSH_TO_CW = False
    return temp


def getUtilization(handle):
    try:
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_util = str(util.gpu)
        mem_util = str(util.memory)
    except NVMLError as err:
        error = handleError(err)
        gpu_util = error
        mem_util = error
        PUSH_TO_CW = False
    return util, gpu_util, mem_util


def logResults(i, util, gpu_util, mem_util, powDrawStr, temp):
    try:
        gpu_logs = open(TMP_FILE_SAVED, 'a+')
        writeString = str(i) + ',' + gpu_util + ',' + mem_util + ',' + powDrawStr + ',' + temp + '\n'
        gpu_logs.write(writeString)
    except:
        print("Error writing to file ", gpu_logs)
    finally:
        gpu_logs.close()
    if (PUSH_TO_CW):
        MY_DIMENSIONS=[
                    {
                        'Name': 'GPUNumber',
                        'Value': str(i)
                    },
                    {
                        'Name': 'InstanceId',
                        'Value': INSTANCE_ID
                    }
                ]
        cloudwatch.put_metric_data(
            MetricData=[
                {
                    'MetricName': 'GPUUsage',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'Percent',
                    'StorageResolution': store_reso,
                    'Value': util.gpu
                },
                {
                    'MetricName': 'MemoryUsage',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'Percent',
                    'StorageResolution': store_reso,
                    'Value': util.memory
                },
                {
                    'MetricName': 'PowerUsageWatts',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'None',
                    'StorageResolution': store_reso,
                    'Value': float(powDrawStr)
                },
                {
                    'MetricName': 'TemperatureC',
                    'Dimensions': MY_DIMENSIONS,
                    'Unit': 'None',
                    'StorageResolution': store_reso,
                    'Value': int(temp)
                },            
        ],
            Namespace=my_NameSpace
        )
    
    
nvmlInit()
deviceCount = nvmlDeviceGetCount()


def main():
    try:
        while True:
            PUSH_TO_CW = True
            # Find the metrics for each GPU on instance
            for i in range(deviceCount):
                handle = nvmlDeviceGetHandleByIndex(i)

                powDrawStr = getPowerDraw(handle)
                temp = getTemp(handle)
                util, gpu_util, mem_util = getUtilization(handle)
                logResults(i, util, gpu_util, mem_util, powDrawStr, temp)

            sleep(sleep_interval)

    finally:
        nvmlShutdown()

if __name__=='__main__':
    main()



