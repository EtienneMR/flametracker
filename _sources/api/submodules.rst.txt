Submodules
==========

The FlameTracker module is divided into several submodules, each responsible for specific functionality.

The :doc:`flametracker` module should cover all needs.

flametracker.core
------------------------
Core functionality for managing trackers and actions.

.. note::
   This submodule contains utility functions and classes that are re-exported by the main module.

   All members of this submodule are intended to be accessed through the main module's namespace.

.. automodule:: flametracker.core
   :members:
   :undoc-members:
   :no-index:

flametracker.rendering
-----------------------------
Handles rendering of tracked actions into visual representations like flamegraphs.

.. automodule:: flametracker.rendering
   :members:
   :undoc-members:

flametracker.tracking
----------------------------
Defines the structure and behavior of action nodes used for tracking.

.. automodule:: flametracker.tracking
   :members:
   :undoc-members:

flametracker.types
-------------------------
Defines type annotations and utility types used across the library.

.. automodule:: flametracker.types
   :members:
   :undoc-members:

flametracker.UntrackedActionNode
---------------------------------------
Fallback implementation for actions when no tracker is active.

.. automodule:: flametracker.UntrackedActionNode
   :members:
   :undoc-members:
