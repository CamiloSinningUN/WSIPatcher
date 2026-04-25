Contributing
============

Contributions are welcome! Please follow these guidelines.

Development Setup
-----------------

.. code:: bash

   git clone https://github.com/CamiloSinningUN/GlassCut.git
   cd GlassCut
   uv sync --group dev

Building Documentation
----------------------

.. code:: bash

   cd docs
   sphinx-apidoc -o api ../glasscut
   make html

Pull Request Process
--------------------

1. Fork the repository and create a feature branch
2. Add tests for any new functionality
3. Ensure all tests pass and linting is clean
4. Update documentation if needed
5. Submit a pull request
