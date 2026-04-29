Extension services
==================

There are a few official extensions to LTI 1.3, providing extra services.

.. todo::

    Say what claims you need to make when registering, in order to use these extensions.

The assignments and grades service
----------------------------------

The assignments and grades service (AGS) provides a mechanism for tools to read and write grades corresponding to LTI resources.

See the `Assignment and Grade Services specification <https://www.imsglobal.org/spec/lti-ags/v2p0>`_.

.. todo::

   Explain line items.

   Something about how different platforms handle line items, e.g. Brightspace being bonkers.

.. automodule:: pylti1p3.assignments_grades
   :members:

.. automodule:: pylti1p3.grade
   :members:

Line items
^^^^^^^^^^

.. automodule:: pylti1p3.lineitem
   :members:

The course groups service
-------------------------

The course groups service provides LTI tools to query the groups available in the course, and the students belonging to them.

See the `Course Groups Service specification <https://www.imsglobal.org/spec/lti-gs/v1p0>`_.

.. automodule:: pylti1p3.course_groups
   :members:

Deep linking
------------

A deep link LTI launch shows the user an interface for choosing the content that will be linked to through the web interface.
The tool shows a selection interface to the user, usually inside an iframe embedded in the platform, and then causes the browser to post the information back to the platform, which will configure the resource link.

See the `Deep Linking specification <https://www.imsglobal.org/spec/lti-dl/v2p0/>`_.

.. automodule:: pylti1p3.deep_link
   :members:

.. automodule:: pylti1p3.deep_link_resource
   :members:

The names and roles provisioning service
----------------------------------------

The names and roles provisioning service (NRPS) provides a mechanism for tools to request a list of users and their roles within a context.

See the `names and roles provisioning service specification <https://www.imsglobal.org/spec/lti-nrps/v2p0>`_.

.. automodule:: pylti1p3.names_roles
   :members:

