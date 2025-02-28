<?php

namespace App\DTO;

class ServerInfoDTO
{
    public function __construct(
        public string $php_version,
        public array $server_info,
    ) {}
}