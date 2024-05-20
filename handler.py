import boto3
from botocore.exceptions import ClientError

# Initialize clients for Control Tower and Organizations
controltower_client = boto3.client('controltower', region_name='ap-south-1')
organizations_client = boto3.client('organizations', region_name='ap-south-1')

def lambda_handler(event, context):
    try:
        # Define the OU ID and baseline version
        ou_id = 'ou-by4j-vdgf30ip'
        baseline_version = '4.0'

        # Step 1: Get the Identity Center Baseline ARN
        identity_center_baseline_arn = get_identity_center_baseline_arn()
        print(f"Identity Center Baseline ARN: {identity_center_baseline_arn}")

        # Step 2: Get the Enabled Identity Center Baseline ARN
        enabled_identity_center_baseline_arn = get_enabled_identity_center_baseline_arn(identity_center_baseline_arn)
        print(f"Enabled Identity Center Baseline ARN: {enabled_identity_center_baseline_arn}")

        # Step 3: Get the ARN of the target OU
        ou_arn = describe_organizational_unit(ou_id)
        print(f"Organizational Unit ARN: {ou_arn}")

        # Step 4: Get the ARN of the AWSControlTowerBaseline baseline
        control_tower_baseline_arn = get_control_tower_baseline_arn()
        print(f"AWS Control Tower Baseline ARN: {control_tower_baseline_arn}")

        # Step 5: Register or Re-register the OU with Control Tower
        if not is_ou_registered(ou_arn):
            print("Registering OU...")
            enable_baseline(control_tower_baseline_arn, baseline_version, ou_arn, enabled_identity_center_baseline_arn)
        else:
            print("Re-registering OU...")
            enabled_baseline_arn = get_enabled_baseline_arn_for_ou(ou_arn)
            reset_enabled_baseline(enabled_baseline_arn)

        return {
            'statusCode': 200,
            'body': "OU registration or re-registration completed successfully!"
        }

    except ClientError as e:
        print("ClientError:", e.response['Error']['Message'])
        return {
            'statusCode': 500,
            'body': f"ClientError occurred: {e.response['Error']['Message']}"
        }
    except Exception as e:
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'body': f"Exception occurred: {str(e)}"
        }

def get_identity_center_baseline_arn():
    response = controltower_client.list_baselines()
    baselines = response.get('baselines', [])
    for baseline in baselines:
        if baseline.get('name') == 'IdentityCenterBaseline':
            return baseline.get('arn')
    raise ValueError("Identity Center Baseline not found")

def get_enabled_identity_center_baseline_arn(identity_center_baseline_arn):
    response = controltower_client.list_enabled_baselines()
    enabled_baselines = response.get('enabledBaselines', [])
    for enabled_baseline in enabled_baselines:
        if enabled_baseline.get('baselineIdentifier') == identity_center_baseline_arn:
            return enabled_baseline.get('arn')
    raise ValueError("Enabled Identity Center Baseline not found")

def describe_organizational_unit(ou_id):
    response = organizations_client.describe_organizational_unit(
        OrganizationalUnitId=ou_id
    )
    return response['OrganizationalUnit']['Arn']

def get_control_tower_baseline_arn():
    response = controltower_client.list_baselines()
    baselines = response.get('baselines', [])
    for baseline in baselines:
        if baseline.get('name') == 'AWSControlTowerBaseline':
            return baseline.get('arn')
    raise ValueError("AWS Control Tower Baseline not found")

def enable_baseline(baseline_arn, baseline_version, ou_arn, enabled_identity_center_baseline_arn=None):
    try:
        parameters = []
        if enabled_identity_center_baseline_arn:
            parameters.append({
                'key': 'IdentityCenterEnabledBaselineArn',
                'value': enabled_identity_center_baseline_arn
            })

        response = controltower_client.enable_baseline(
            baselineIdentifier=baseline_arn,
            baselineVersion=baseline_version,
            targetIdentifier=ou_arn,
            parameters=parameters
        )
        print("enable_baseline response:", response)
    except ClientError as e:
        print(f"Failed to enable baseline: {e.response['Error']['Message']}")
        raise

def is_ou_registered(ou_arn):
    response = controltower_client.list_enabled_baselines()
    enabled_baselines = response.get('enabledBaselines', [])
    for enabled_baseline in enabled_baselines:
        if enabled_baseline.get('targetIdentifier') == ou_arn:
            return True
    return False

def get_enabled_baseline_arn_for_ou(ou_arn):
    response = controltower_client.list_enabled_baselines()
    enabled_baselines = response.get('enabledBaselines', [])
    for enabled_baseline in enabled_baselines:
        if enabled_baseline.get('targetIdentifier') == ou_arn:
            return enabled_baseline.get('arn')
    raise ValueError(f"Enabled baseline for OU {ou_arn} not found")

def reset_enabled_baseline(enabled_baseline_arn):
    try:
        response = controltower_client.reset_enabled_baseline(
            enabledBaselineIdentifier=enabled_baseline_arn
        )
        print("reset_enabled_baseline response:", response)
    except ClientError as e:
        print(f"Failed to reset enabled baseline: {e.response['Error']['Message']}")
        raise
