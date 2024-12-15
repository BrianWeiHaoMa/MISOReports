def pytest_addoption(parser):
    parser.addoption(
        "--datetime-increments-limit",
        action="store",              
        type=int,
        default=25,      
        help="The maximum amount of increments to datetime while downloading from URLs",
    )

    parser.addoption(
        "--number-of-dfs-to-stop-at",
        action="store",              
        type=int,
        default=3,      
        help="The maximum amount of increments dfs to test for a single report",
    )