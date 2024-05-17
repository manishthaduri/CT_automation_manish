import boto3
from botocore.exceptions import ClientError

# Initialize clients for Control Tower and Organizations
controltower_client = boto3.client('controltower', region_name='ap-south-1')
organizations_client = boto3.client('organizations', region_name='ap-south-1')

def lambda_handler(event, context):
    try:
        # Step 1: List Identity Center Baseline ARN
        identity_center_baseline_response = controltower_client.list_baselines()
        print("identity_center_baseline_response", identity_center_baseline_response)
        
        identity_center_baseline_arn = None
        for baseline in identity_center_baseline_response['baselines']:
            if baseline['name'] == 'IdentityCenterBaseline':
                identity_center_baseline_arn = baseline['arn']
                break
        
        if identity_center_baseline_arn is None:
            raise ValueError("Identity Center Baseline not found")

        # Step 2: List Enabled Identity Center Baseline ARN
        enabled_baseline_response = controltower_client.list_enabled_baselines()
        print("enabled_baseline_response", enabled_baseline_response)
        
        enabled_baseline_arn = None
        for enabled_baseline in enabled_baseline_response['enabledBaselines']:
            if enabled_baseline['baselineIdentifier'] == identity_center_baseline_arn:
                enabled_baseline_arn = enabled_baseline['arn']
                break
        
        if enabled_baseline_arn is None:
            raise ValueError("Enabled Identity Center Baseline not found")

        # Step 3: Describe Organizational Unit
        ou_arn = describe_organizational_unit('ou-by4j-9pxfa87b')

        # Step 4: List AWS Control Tower Baseline ARN
        aws_control_tower_baseline_response = controltower_client.list_baselines()
        print("aws_control_tower_baseline_response", aws_control_tower_baseline_response)
        
        aws_control_tower_baseline_arn = None
        for baseline in aws_control_tower_baseline_response['baselines']:
            if baseline['name'] == 'AWSControlTowerBaseline':
                aws_control_tower_baseline_arn = baseline['arn']
                break
        
        if aws_control_tower_baseline_arn is None:
            raise ValueError("AWS Control Tower Baseline not found")

        # Step 5: Enable AWS Control Tower Baseline
        controltower_client.enable_baseline(
            baselineIdentifier=aws_control_tower_baseline_arn,
            baselineVersion='4.0',
            targetIdentifier=ou_arn,
            parameters=[
                {
                    'key': 'IdentityCenterEnabledBaselineArn',
                    'value': enabled_baseline_arn
                }
            ]
        )

        return "Baseline enabled successfully!"
    except ClientError as e:
        print("ClientError:", e.response['Error']['Message'])
        return f"ClientError occurred while enabling baseline: {e.response['Error']['Message']}"
    except Exception as e:
        print("Exception:", str(e))
        return f"Exception occurred while enabling baseline: {str(e)}"

def describe_organizational_unit(ou_id):
    response = organizations_client.describe_organizational_unit(
        OrganizationalUnitId=ou_id
    )
    return response['OrganizationalUnit']['Arn']
