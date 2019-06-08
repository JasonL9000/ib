import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
   name='ib',
   version='0.1',
   scripts=['ib'] ,
   author="Jason Lucas",
   author_email="jasonl9000@gmail.com",
   description="A build tool that automatically resolves included sources.",
   long_description=long_description,
   long_description_content_type="text/markdown",
   url="https://github.com/hooddanielc/ib-tools",
   packages=setuptools.find_packages(),
   classifiers=[
     "Programming Language :: Python :: 2",
     "Operating System :: OS Independent",
   ],
)
