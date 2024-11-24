def pytest_addoption(parser):
    parser.addoption(
        "--datetime-increments-limit",
        action="store",              
        type=int,
        default=300,      
        help="The maximum amount of increments to datetime while downloading from URLs",
    )