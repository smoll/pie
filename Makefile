default: env

env: env/bin/activate

env/bin/activate: requirements.txt
	test -d env || virtualenv env
	. env/bin/activate; pip install -Ur requirements.txt
	touch env/bin/activate

spike: env
	. env/bin/activate; python spike.py

debug: env
	. env/bin/activate; python crawler.py

pre: env
	. env/bin/activate; python batch/pre.py

start: env
	. env/bin/activate; python batch/serial.py

post: env
	. env/bin/activate; python batch/post.py

stats: env
	. env/bin/activate; python stats.py

clean:
	rm -rf env
	find -iname "*.pyc" -delete
