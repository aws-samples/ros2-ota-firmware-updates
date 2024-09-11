#!/bin/bash
set -e

export AWS_PAGER=""

function create_thing() {
    THING_NAME=$1
    echo "Creating Thing $THING_NAME"
    # THING_NAME=device-thing-0
    # echo "Creating Thing $THING_NAME"
    echo "Checking if Thing $THING_NAME exists"
    if aws iot describe-thing --thing-name $THING_NAME --query "thingName" --output text | grep -q $THING_NAME; then
        echo "Thing $THING_NAME exists"
        return
    fi
    echo "Thing $THING_NAME does not exist, creating it"
    aws iot create-thing --thing-name $THING_NAME

    mkdir -p certs/${THING_NAME}
    echo "Generating certs"
    CERT_ARN=$(aws iot create-keys-and-certificate --set-as-active --certificate-pem-outfile certs/${THING_NAME}/device.pem.crt --public-key-outfile certs/${THING_NAME}/public.pem.key --private-key-outfile certs/${THING_NAME}/private.pem.key --query "certificateArn" --output text)
    wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O certs/${THING_NAME}/AmazonRootCA1.pem
    echo "Generated certificate ARN: $CERT_ARN"

    echo "Attaching Thing $THING_NAME to principal $CERT_ARN"
    aws iot attach-thing-principal --thing-name $THING_NAME --principal $CERT_ARN

    IOT_POLICY_NAME=device-thing-policy

    echo "Attempting to fetch IoT policy $IOT_POLICY_NAME"
    if aws iot list-policies --query "policies[?policyName=='$IOT_POLICY_NAME'].policyName" --output text | grep -q $IOT_POLICY_NAME; then
        echo "IoT policy '$IOT_POLICY_NAME' exists"
    else
        echo "IoT policy '$IOT_POLICY_NAME' does not exist"
        echo "Creating IoT policy $IOT_POLICY_NAME"
        aws iot create-policy --policy-name $IOT_POLICY_NAME --policy-document file://policies/device-iot-policy.json
    fi


    echo "Attaching IoT policy $IOT_POLICY_NAME to principal $CERT_ARN"
    aws iot attach-policy --policy-name $IOT_POLICY_NAME --target $CERT_ARN
}

NUM_DEVICES=2
DEVICE_TYPES=("firmware" "agent")

for device_num in $(seq 1 $NUM_DEVICES)
do
    for device_type in ${DEVICE_TYPES[@]}
    do
    THING_NAME="device-thing-${device_num}-${device_type}"
    create_thing $THING_NAME
    done
done