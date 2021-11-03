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

### Port forwarding (See TensorBoard in your local browser)

Open a terminal on your local machine, set up port forwarding

```
ssh -L localhost:8895:localhost:8893 <username>@96.76.203.7
```

`8895` here is the port on your local machine to communicate with the remote instance. `8893` HAS TO BE the port on the remote instance used in the previous "Launch Tensorboard" step.

Then on your local machine, open a browser and go to `http://localhost:8895`


## Setup VS Code

### Preparing
1. Download SSH, Python, and Jupiter extensions in VS Code
2. Log into the machine using SSH extension in VS Code (find the Remote Explorer Icon on the left side)

### Setting up Jupiter Notebook in VS Code
3. Open a Terminal outside VS Code and log into the machine using ssh
4. Go into your virtual environment and open jupyter notebook using `jupyter notebook --port=8892`
5. Open the Command Palette (Cmd+Shift+P) and write 'remote' (to find “Jupiter: Specify local or remote Jupiter server for connections”)
6. Go to the right lower corner and click on "Jupyter Server: Remote"
7. Click on Existing and Confirm that the URI is the same that shows up on the terminal
8. Open a notebook (Go to File, Open, and find your notebook)
9. Change the kernel at right upper corner (“Select Kernel”) with your virtualenv
10. Run the notebook

### Setting up Tensorboard in VS Code
10. Open a new Terminal outside VS Code and log into the machine using ssh 
11. Open tensor board using `tensorboard --logdir log --port 8893`
12. Open the Command Palette and find "Python: Launch Tensorboard" or Click on Launch Tensorboard Session in your notebook.
13. Click on Select another folder and find the directory of your 'log' folder
