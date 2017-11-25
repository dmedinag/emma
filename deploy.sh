#!/usr/bin/env bash

######## CHECK REQUIREMENTS

# docker
if ! which docker > /dev/null; then echo "Sorry, you need to have docker installed before proceeding" >&2; return -1; fi
# bash 4.0
if ((BASH_VERSINFO[0] < 4)); then echo "Sorry, you need at least bash-4.0 to run this script." >&2; return -1; fi
# awscli
if ! aws --version >& /dev/null; then echo "Sorry, you need to have awscli installed before proceeding" >&2; return -1; fi

######## SET UP ENVIRONMENT

project=$1
test_only=$2
valid_project=0
docker_image="lambdatest"
bucket=acoutech

red='\033[0;31m'
gr='\033[1;32m'
nc='\033[0m'
bold=$(tput bold)
thin=$(tput sgr0)

######## CHECK PARAMS

for possible_project in */
do
    if [ "$project" == "${possible_project/\//}" ]
    then
        valid_project=1
    fi
done

if [ "$valid_project" == "0" ]
then
    echo "usage: $0 <project>"
    echo "Select a <project> in:"
    for possible_project in */
    do
        echo " - ${possible_project/\//}"
    done
    exit
fi

######## EXECUTION

echo
echo "$bold******** TESTING $project ********$thin"
echo

echo
echo "$bold*** BUILDING DOCKER IMAGE ***$thin"
echo

docker build -t $docker_image .

echo
echo "$bold*** RUNNING LOCAL TESTS ***$thin"
echo

if docker run -it --mount type=bind,src="$(PWD)"/"$project",target=/opt/,readonly $docker_image python test.py
then
    if [ "$test_only" == "test_only" ]
    then
        echo
        echo -e "$gr$bold########## TESTING SUCCEEDED ########## $thin$nc"
        echo
        exit
    fi

    echo
    echo "$bold******** DEPLOYING $project ********$thin"
    echo

    echo "Compressing code"
    cd $project
    zip -q -r -4 ${project,,} *
    mv ${project,,}.zip ../
    cd ..
    echo "Done"

    echo "Uploading code to s3"
    aws s3 cp ${project,,}.zip s3://${bucket}/${project,,}/${project,,}.zip
    echo "Done"

    echo "Updating code in lambda"
    aws lambda update-function-code --function-name $project --s3-bucket ${bucket} --s3-key ${project,,}/${project,,}.zip
    echo "Done"

    echo "Cleaning up"
    rm -rf ${project,,}.zip
    echo "Done"

    echo
    echo -e "$gr$bold########## DEPLOYMENT SUCCEEDED ########## $thin$nc"
    echo

else
    echo
    echo -e "$red$bold########## SOME TESTS FAILED, DEPLOYMENT NOT ALLOWED ########## $thin$nc"
    echo
fi
