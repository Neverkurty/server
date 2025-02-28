<?php

namespace App\DTO;

class ClientInfoDTO
{
    public function __construct(
        public string $ip,
        public string $user_agent,
    ) {}
}