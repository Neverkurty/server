<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class InfoController extends Controller
{
    public function serverInfo()
    {
        return response()->json([
            'php_version' => phpversion(),
            'server_info' => $_SERVER,
        ]);
    }

    public function clientInfo(Request $request)
    {
        return response()->json([
            'ip' => $request->ip(),
            'user_agent' => $request->userAgent(),
        ]);
    }

    public function databaseInfo()
    {
        $tables = DB::select('SHOW TABLES');
        return response()->json([
            'tables' => $tables,
        ]);
    }
}
