sudo add-apt-repository ppa:jonathonf/python-3.6
sudo apt-get update
 1994  sudo apt-get install python3.6
 1995  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.5 1
 1996  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 2
 1997  sudo update-alternatives --config python3
 1998  python3 -V


sudo apt-get install python3.6-venv

python3 -m venv .venv/morphophonology_optimality_venv/

wget https://pypi.python.org/packages/65/d5/0f44e7645592905a314041f15700a0ba04befe198f939245beebba4d63d9/FAdo3-1.0.tar.gz#md5=8ce8febff71eb4ff8596c84d134dcd10
tar -xvzf FAdo3-1.0.tar.gz
cd FAdo3-1.0
sudo python3 setup.py install


 source ~/.venv/morphophonology_optimality_venv/bin/activate