# Service discovery

Tool for the discovery of the ip and port on which one service is listening. If several services of the same type (same name) are registered, a synchronization process will be generated between them and only one will obtain the mastery of the service, the rest will remain as a backup in case the service should fail.
