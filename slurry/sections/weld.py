"""
The weld module implements the weld function that connects Sections together and
returns the async iterable output.
"""

from typing import Any, AsyncIterable, Sequence, Tuple, Union, NewType

import trio

from .abc import Section, ThreadSection, ProcessSection
from .pump import pump

SectionSequence = NewType(
    'SectionSequence',
    Sequence[Union[AsyncIterable[Any], Section, ThreadSection, ProcessSection, Tuple]])

def weld(nursery, *sections: SectionSequence) -> AsyncIterable[Any]:
    """
    Connects the individual parts of a ``SectionSequence`` together and starts pumps for
    individual Sections. It returns an async iterable which yields results of the sequence.

    :param :class:`trio.Nursery` nursery: The nursery that runs individual pipeline section pumps.
    :param SectionSequence sections: A sequence of pipeline sections.
    """
    section_input = None
    output = None
    for section in sections:
        if isinstance(section, (Section, ThreadSection, ProcessSection)):
            section_output, output = trio.open_memory_channel(0)
            nursery.start_soon(pump, section, section_input, section_output)
        elif isinstance(section, tuple):
            if section_input:
                output = weld(nursery, section_input, *section)
            else:
                output = weld(nursery, *section)
        else:
            if output:
                raise ValueError('Invalid pipeline section.', section)
            output = section
        section_input = output

    return output
