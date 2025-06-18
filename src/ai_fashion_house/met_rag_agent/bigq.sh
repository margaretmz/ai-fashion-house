bq mk --connection --location=us --project_id=build-with-ai-project \
    --connection_type=CLOUD_RESOURCE met_data_conn

bq --location=US mk -d \
 --description "Met data for the adk hackathon" \
 met_data

bq show --connection build-with-ai-project.us.met_data_conn