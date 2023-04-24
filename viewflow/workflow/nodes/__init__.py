"""Base workflow node set."""

from .end import End, EndActivation
from .func import Function, FunctionActivation
from .handle import Handle, HandleActivation
from .if_gate import If, IfActivation
from .job import AbstractJob, AbstractJobActivation
from .join import Join, JoinActivation
from .obsolete import Obsolete, ObsoleteActivation
from .split import Split, SplitActivation, SplitFirst
from .start import Start, StartHandle, StartActivation
from .subprocess import StartSubprocess, Subprocess, NSubprocess
from .switch import Switch, SwitchActivation
from .view import ViewActivation, View

__all__ = (
    "AbstractJob",
    "AbstractJobActivation",
    "End",
    "EndActivation",
    "Function",
    "FunctionActivation",
    "Handle",
    "HandleActivation",
    "If",
    "IfActivation",
    "Join",
    "JoinActivation",
    "NSubprocess",
    "Obsolete",
    "ObsoleteActivation",
    "Split",
    "SplitActivation",
    "SplitFirst",
    "Start",
    "StartActivation",
    "StartHandle",
    "StartSubprocess",
    "Subprocess",
    "Switch",
    "SwitchActivation",
    "View",
    "ViewActivation",
)
