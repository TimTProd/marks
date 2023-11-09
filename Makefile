build:
	docker build . -t marks_bot
	docker run -d --restart=always -v bot_vol:/usr/src/app/bd --name marks_bot marks_bot

test:
	docker build . -t test_bot
	docker run -d --name test_bot test_bot

testupdate:
	docker kill test_bot
	docker rm test_bot
	docker rmi test_bot
	docker build . -t test_bot
	docker run -d --name test_bot test_bot

update:
	docker kill marks_bot
	docker rm marks_bot
	docker rmi marks_bot
	docker build . -t marks_bot
	docker run -d --restart=always -v bot_vol:/usr/src/app/bd --name marks_bot marks_bot

teststop:
	docker kill test_bot
	docker rm test_bot
	docker rmi test_bot

stop:
	docker kill marks_bot
	docker rm marks_bot
	docker rmi marks_bot
