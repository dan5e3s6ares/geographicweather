<h1 align="center">Weather From Geo InterFace - AWS Lambda Microservice</h1>

<br>

## About ##

This repository generates a PDF file and saves it in a RestAPI database, with the 1 year history of Temperature, Precipitation, and Wind from the closest weather station to the geographic map provided. It also returns the average ground water of the last year using satellite images.
This repository is ready to be implemented in an AWS Lambda Function.

## Installing Dependencies ##
```bash
## Build Docker Image
$ docker build -t climatempo .

## AWS Authetication
$ aws ecr get-login-password --region sa-east-1 | docker login --username AWS --password-stdin XXXXXXXXXXXXXXXX.dkr.ecr.sa-east-1.amazonaws.com

## Create Repository
$ aws ecr create-repository --repository-name climatempo --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE

## Copy to AWS the Repository:
$ docker tag  climatempo:latest XXXXXXXXXXXXXXX.dkr.ecr.sa-east-1.amazonaws.com/climatempo:latest
$	docker push XXXXXXXXXXXXXXX.dkr.ecr.sa-east-1.amazonaws.com/climatempo:latest

## Start in AWS Lambda the Repository

## Payload
data = {'ponto': ponto.__geo_interface__ , 'url': 'http://databaseAPI/pages/', 
        'token': 'TOKEN', 'cod': 'flerifbwet7864poigjfgdbçcr287456brtgfgh', 'relid' : relid}


```
