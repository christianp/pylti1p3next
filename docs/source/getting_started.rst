Getting started
===============

``pylti1p3next`` helps to manage the interaction between your LTI :term:`tool` and a :term:`platform`, using the LTI 1.3 protocol.


See the `LTI 1.3 specification <https://www.imsglobal.org/spec/lti/v1p3/>`__ for a description of how the protocol works.



Registration
------------

You must register your tool with the platform.
Some platforms support dynamic registration, while others require you to enter the connection details manually.

Communication between the tool and platform is signed using RSA keys. You must serve a keyset in JWKS format so that the platform can retrieve your public key. 

The platform also needs from your tool:

* A URL to initiate OIDC logins.
* A list of URLs that you can redirect a launch to, after login. It's often easiest to have a single launch URL, and use launch parameters to determine where to redirect them.


Dynamic registration
^^^^^^^^^^^^^^^^^^^^

See the `dynamic registration specification <https://www.imsglobal.org/spec/lti-dr/v1p0>`_.

For dynamic registration, you give the platform a URL which it should call to begin the registration process.
In practice, you might want to pre-authorise a registration, in which case the token should contain some kind of token that you use to validate the registration.

When the platform requests your dynamic registration URL, create an instance of :py:class:`pylti1p3.dynamic_registration.DynamicRegistration` using the request object.
There is a Django-specific subclass :py:class:`pylti1p3.contrib.django.lti1p3_tool_config.dynamic_registration.DjangoDynamicRegistration` which stores registration information using Django's ORM.

Get the platform's OpenID configuration using :py:func:``pylti1p3.dynamic_registration.DynamicRegistration.get_openid_configuration()`` - this makes an HTTP request to the platform - and then get the platform name with :py:func:``pylti1p3.dynamic_registration.DynamicRegistration.get_platform_name()``.

The platform's requested LTI configuration is in the ``https://purl.imsglobal.org/spec/lti-platform-configuration`` claim of its OpenID configuration.
Use that to check that the platform supports all of the features that you need.

Manual registration
^^^^^^^^^^^^^^^^^^^

On giving your tool's details to the platform, it should give you a deployment ID which it will include in every LTI launch.
Your tool should use that deployment ID to validate launch messages.
