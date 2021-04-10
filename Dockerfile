from jkjh1jkjh1/target-base

run mkdir /home/hacker/phpil
copy testing/php.ini /home/hacker/php.ini
run sudo pip uninstall -y ipython
run pip install ipython clang
run mkdir /tmp/coverages
run mv /home/hacker/targets/php-phpil-asan-src /home/hacker/
run rm -rf /home/hacker/targets/*
run mv /home/hacker/php-phpil-asan-src /home/hacker/targets/
copy PhpIL /home/hacker/phpil/PhpIL
copy testing /home/hacker/phpil/testing

# cmd ["/bin/bash"]
cmd ["python", "/home/hacker/phpil/testing/main.py"]
