FROM python

ADD src/* /opt/
WORKDIR /opt

RUN pip install -r requirement.txt

CMD ["python", "main.py"]
