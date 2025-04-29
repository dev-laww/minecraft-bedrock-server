docker compose stop

# wait for the containers to stop

while docker container ps -q | grep -q .; do
    sleep 1
done

# shut down machine

#echo "Shutting down the machine..."
#
#powershell Stop-Computer -Force