# Web Novel To Audio Txt

## Chrome Extension to crawl syosetu novels to audio text files
- ncode and nocturn novels

## TODO List
- use scrapyd to deploy scrapy spider to localhost/docker container to crawl novel into jsonline files
	- can deploy new novel url, list of url to crawl when you want
	- can be automated to crawl 
- use scrapydweb to manage different spiders
- yper to make commmand line app to unpack jl files into text files ready to convert to audio

## Scrapyd Install Instructions
- Install Scrapyd: `pip install scrapyd`
- Start Scrapyd with: `scrapyd`
- Install Scrapyd-client: `pip install scrapyd-client`
- Deploy Scrapy project to Scrapyd on another terminal: `scrapyd-deploy`

## Locally Run Instructions
- Run Scrapyd with the command: `scrapyd`
- Deploy Scrapy project with Scrapyd to server/localhost `http://127.0.0.1:6800/` on another terminal with: `scrapyd-deploy`
- Once the project is deployed, schedule spider run using commands or with REST API:
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider`
- Monitor and manage spider with the Scrapyd API:
  - `curl http://localhost:6800/listjobs.json?project=scrapyd_webnovel_jsonl`

## Refresh Scrapyd Server
- Stop Scrapyd server: Press `Ctrl+C` in the terminal where Scrapyd is running
- Start Scrapyd server again: `scrapyd`
- Redeploy project to update without restarting: `scrapyd-deploy`

## Create egg file and deploy to localhost/docker container
# Create egg file - Make sure you're in the root directory of the tutorial project, where the scrapy.cfg resides.
'scrapyd-deploy --build-egg scrapyd_webnovel_jsonl.egg'

# Deploy egg file version - change with your project name
'curl http://localhost:6800/addversion.json -F project=scrapyd_webnovel_jsonl -F version=r1 -F egg=@scrapyd_webnovel_jsonl.egg'

# To schedule the execution of some spider, use the scrapyd API:
'curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider'


## Curl Instructions
- Very scrapyd is running `curl http://localhost:6800/daemonstatus.json`
- List versions: `curl http://localhost:6800/listversions.json?project=scrapyd_webnovel_jsonl`
- Delete old versions: `curl http://localhost:6800/delversion.json -d project=scrapyd_webnovel_jsonl -d version=v1`
- Use curl to get latest spider version, before set new schedule: latest_version=$(curl -s http://localhost:6800/listversions.json?project=scrapyd_webnovel_jsonl | jq -r '.versions[0]')
- curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d version=$latest_version -d start_urls=https://ncode.syosetu.com/n4750dy/
- cancel schedule: `curl http://localhost:6800/cancel.json -d project=scrapyd_webnovel_jsonl -d job={job_id}`

- Schedule spider run: 
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider`

  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls=https://ncode.syosetu.com/n5194gp/`

  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls="https://ncode.syosetu.com/n4750dy/,https://ncode.syosetu.com/n8611bv/`

  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=nocturne_spider`

- curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d version=1735855513 -d start_urls=https://ncode.syosetu.com/n0763jx/

curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls=https://ncode.syosetu.com/n0763jx/

## Docker Instructions
# build docker image:
#docker build -t scrapyd-webnovel:latest -f ../docker/dockerfile .
`docker build -t scrapyd-webnovel -f ../dockerfile .`

# run docker container from image:
- `docker run --name container_name -d -p 6800:6800 -v path_local_folder:path_container_folder image_name`
# example: `docker run --name scrapyd-webnovel -d -p 6800:6800 -v c://Users//BaoTN//Documents//scraped_items:/var/lib/scrapyd/items scrapyd-webnovel`


