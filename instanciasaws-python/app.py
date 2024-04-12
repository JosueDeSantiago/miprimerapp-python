from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import boto3

app = Flask(__name__)

# Conectarse a AWS
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')

# Obtener instancias EC2
response = ec2_client.describe_instances()
instances = response['Reservations']

# Calcular el tiempo hace 24 horas
end_time = datetime.now()
start_time = end_time - timedelta(hours=24)

# Lista para almacenar los promedios de uso de CPU
cpu_usage_averages = []

# Iterar sobre las instancias y obtener métricas de CPU
for instance in instances:
    instance_id = instance['Instances'][0]['InstanceId']
    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=['Average']
    )
    if 'Datapoints' in response:
        datapoints = response['Datapoints']
        if datapoints:
            cpu_average = sum(point['Average'] for point in datapoints) / len(datapoints)
            cpu_usage_averages.append(cpu_average)

# Calcular el promedio general de uso de CPU
overall_cpu_average = sum(cpu_usage_averages) / len(cpu_usage_averages) if cpu_usage_averages else 0

@app.route('/')
def index():
    instances = ec2.instances.all() 
    return render_template('index.html', cpu_average=overall_cpu_average, instances=instances)

@app.route('/action', methods=['POST'])
def action():
    instance_id = request.form.get('id')
    action = request.form.get('action')
    
    instance = ec2.Instance(instance_id)
    
    if action == 'Detener':
        instance.stop()
    elif action == 'Iniciar':
        instance.start()    
 
    return redirect(url_for('index'))