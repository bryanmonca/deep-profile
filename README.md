# deep-profile


## Setup on X2GO remote desktop

```
git clone https://github.com/bryanmonca/deep-profile.git


virtualenv -p /usr/bin/python3.6 venv
. venv/bin/activate
pip install -r requirements.txt
ipython kernel install --user --name=venv
```


### Launch Jupyter Notebook

Use a different port is the default one is occupied.

```
jupyter notebook --port=8892
```

Go to browser, and select "Kernel/Change kernek/venv"


Now you should be able to run the notebook


### Launch Tensorboard

Open a new termninal in X2GO

```
cd path-to-deep-profile
tensorboard --logdir log --port 8893
```

Open a browser and go to


```
localhost:8893
```

Again, use a different port if the default one is occupied by others.
