# Web Novel To Audio Txt

## Chrome Extension to crawl syosetu novels to audio text files
- ncode and nocturn novels

## TODO List
- use scrapyd to deploy scrapy spider to localhost/docker container to crawl novel into jsonline files
	- can deploy new novel url, list of url to crawl when you want
	- can be automated to crawl 
- use scrapydweb to manage different spiders
- yper to make commmand line app to unpack jl files into text files ready to convert to audio

## Instructions
- Run Scrapyd with the command: `scrapyd`
- Deploy Scrapy project with Scrapyd to server/localhost with: `scrapyd-deploy`
- Once the project is deployed, schedule spider run using commands or with REST API:
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider`
- Monitor and manage spider with the Scrapyd API:
  - `curl http://localhost:6800/listjobs.json?project=scrapyd_webnovel_jsonl`

## Scrapyd Instructions
- Install Scrapyd: `pip install scrapyd`
- Start Scrapyd with: `scrapyd`
- Install Scrapyd-client: `pip install scrapyd-client`
- Deploy Scrapy project to Scrapyd on another terminal: `scrapyd-deploy`

## Refresh Scrapyd Server
- Stop Scrapyd server: Press `Ctrl+C` in the terminal where Scrapyd is running
- Start Scrapyd server again: `scrapyd`
- Redeploy project to update without restarting: `scrapyd-deploy`

## Curl Instructions
- List versions: `curl http://localhost:6800/listversions.json?project=scrapyd_webnovel_jsonl`
- Delete old versions: `curl http://localhost:6800/delversion.json -d project=scrapyd_webnovel_jsonl -d version=v1`
- Use curl to get latest spider version, before set new schedule: latest_version=$(curl -s http://localhost:6800/listversions.json?project=scrapyd_webnovel_jsonl | jq -r '.versions[0]')
- curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d version=$latest_version -d start_urls=https://ncode.syosetu.com/n4750dy/

- Schedule spider run: 
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider`
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls=https://ncode.syosetu.com/n4750dy/`
  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls="https://ncode.syosetu.com/n4750dy/,https://ncode.syosetu.com/n8611bv/`

  - `curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=nocturne_spider`

- curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d version=1735855513 -d start_urls=https://ncode.syosetu.com/n0763jx/

curl http://localhost:6800/schedule.json -d project=scrapyd_webnovel_jsonl -d spider=syosetu_spider -d start_urls=https://ncode.syosetu.com/n0763jx/


# run scrapy shell to test scrapy extract which content
# scrapy shell 'https://ncode.syosetu.com/n4750dy/1/'
# Need to move inside the project directory where scrapy.cfg file exists to run the spider
# cd SyosetsuScraper/src/scraper , cd scraper
# scrapy crawl syosetsu -o testjl.jl