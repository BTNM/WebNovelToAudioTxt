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
- run scrapyd with command "scrapyd"
- deploy scrapy project with scrapyd to server/localhost with "scrapyd-deploy"
- Once project is deployed, schedule spider run using commands or with REST API:
	- curl http://localhost:6800/schedule.json -d project=syosetu_spider -d spider=syosetu_spider
- Monitor and manage spider with the Scrapyd API
	- curl http://localhost:6800/listjobs.json?project=syosetu_spider