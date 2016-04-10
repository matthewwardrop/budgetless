FROM codekoala/arch:latest
RUN pacman --noconfirm -Syu
RUN pacman --noconfirm -S python-flask python-pip python-pandas python-numpy python-sqlalchemy python-matplotlib gcc cython python-sympy
MAINTAINER Matthew Wardrop <mister.wardrop@gmail.com>
EXPOSE 5000
RUN pip install gunicorn mintapi plotly parampy
RUN pip install git+https://github.com/matthewwardrop/budgetless.git
CMD budgetless budget.db run --debug
