# Variables definition
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Needed system settings
# https://github.com/SonarSource/docker-sonarqube/blob/master/example-compose-files/sq-with-postgres/docker-compose.yml
sysctl -w vm.max_map_count=524288
sysctl -w fs.file-max=131072

# Launch container
cd $SCRIPTPATH
docker-compose up -d

# Run sonar
cd $SCRIPTPATH/../..
/opt/sonar-scanner-4.6.2.2472-linux/bin/sonar-scanner \
  -Dsonar.projectKey=TrackEditor \
  -Dsonar.sources=TrackApp,TrackEditorWeb,editor \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=admin \
  -Dsonar.password=admin

if [ $? -ne 0 ]; then
echo "Sonar server needs some time to wake up"
fi
