# deep-profile


## Setup on X2GO remote desktop

Login with X2GO. Open a new terminal.

```
git clone https://github.com/bryanmonca/deep-profile.git


virtualenv -p /usr/bin/python3.6 venv
. venv/bin/activate
pip install -r deep-profile/requirements.txt
ipython kernel install --user --name=venv
```


### Launch Jupyter Notebook

```
jupyter notebook --port=8892
```

IMPORTANT: in juypter notebook IDE, select "Kernel/Change kernek/venv"

Use a different port if the default one is occupied.

Now you should be able to run the notebook.

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
