from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import boto3

app = Flask(__name__)

# Conectarse a AWS
ec2 = boto3.resource('ec2')
ec2_client = boto3.client('ec2')
cloudwatch_client = boto3.client('cloudwatch')

def get_instance_name(instance):
    for tag in instance.tags:
        if tag['Key'] == 'Name':
            return tag['Value']
    return 'N/A'

@app.route('/')
def index():
    # Obtener instancias EC2
    instances = ec2.instances.all()
    
    # Calcular el tiempo hace 24 horas
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=24)
    
    # Lista para almacenar los promedios de uso de CPU
    cpu_usage_averages = []
    
    # Iterar sobre las instancias y obtener métricas de CPU
    for instance in instances:    
        instance_id = instance.id
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
    
    return render_template('index.html', cpu_average=overall_cpu_average, instances=instances, get_instance_name=get_instance_name)

@app.route('/action', methods=['POST'])
def action():
    instance_id = request.form.get('id')
    action = request.form.get('action')
    
    instance = ec2.Instance(instance_id)
    
    try:
        if action == 'Detener':
            instance.stop()
        elif action == 'Iniciar':
            instance.start()
    except Exception as e:
        print("Error:", e)
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
