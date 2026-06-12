# RF-Calculator for Inhouse GNSS distribution
GNSS RF Distribution Calculator: A Python script to calculate net gain &amp; loss in local GPS/GNSS networks. Models active antennas, coax cables, splitters, &amp; surge protectors to verify receiver power limits. Perfect for timing network &amp; telecom RF link budgets. Clone, configure your components, &amp; validate signal margins.

GNSS R03
I have been working on a Python-based GNSS RF Network Calculator designed for indoor GNSS signal distribution planning.

The tool is intended to help engineers model and review RF link budgets for GNSS distribution networks inside a building, where signal levels can quickly become difficult to manage because of cable losses, splitters, attenuators, amplifiers, and multiple receiver branches.

Key functions include:

* GNSS frequency-band selection
* Cable loss calculation for common RF cable types
* Splitter, attenuator, amplifier, and connector loss modeling
* Multi-branch RF distribution analysis
* Receiver input-level checking
* Target-level margin calculation
* DC path verification for active GNSS components
* Noise figure estimation
* Amplifier P1dB compression warning
* Graphical network editor
* Drag-and-connect RF path building
* Block diagram visualization
* CSV, JSON, and PNG export

The goal of this tool is to make GNSS RF planning easier, more visual, and more traceable before actual installation or commissioning work begins.

This is especially useful when distributing GNSS signals across long cable runs, multiple workstations, test areas, or lab benches where each branch may have a different cable length, splitter loss, attenuation requirement, or receiver input-level target.

The project is still evolving, but the current direction is to turn the calculator into a practical RF planning and documentation tool for GNSS distribution networks.
