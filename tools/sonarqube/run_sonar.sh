sysctl -w vm.max_map_count=524288
sysctl -w fs.file-max=131072
SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd $SCRIPTPATH
docker-compose up -d

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
