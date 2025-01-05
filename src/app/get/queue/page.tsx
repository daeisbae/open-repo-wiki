'use client';

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle } from 'lucide-react';
import ProcessingItem from "./ProcessingItem";
import React from "react";

export default function Page() {
    const [queue, setQueue] = useState([]);
    const [processing, setProcessing] = useState(null);
    const [processingTime, setProcessingTime] = useState("");
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            const response = await fetch("/api/queue");
            if (response.ok) {
                const { body } = await response.json();
                setQueue(body.queue || []);
                setProcessing(body.processing || null);
                setProcessingTime(body.processingTime || "");
            }
            setIsLoading(false);
        };
        fetchData();
    }, []);

    if (isLoading) {
        return <LoadingSkeleton />;
    }

    return (
        <div className="container mx-auto p-4 h-[calc(80vh-2rem)] flex flex-col space-y-4">
                        <h1>Currently Processing</h1>
                        {processing ? (
                            <ProcessingItem owner={processing.owner} repo={processing.repo} createdAt={processingTime} />
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground">
                                <AlertCircle className="mr-2 h-4 w-4" />
                                No repository currently being processed
                            </div>
                        )}

                        <h1>Queue</h1>
                        {queue.length > 0 ? (
                            <ol className="space-y-2 list-decimal list-inside list-numbered">
                                {queue.map((item, index) => (
                                    <li key={item.repo} className={`p-0 sm:p-2 rounded-md ${index % 2 === 0 ? 'bg-muted' : ''}`}>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium">{item.owner}/{item.repo}</span>
                                        </div>
                                    </li>
                                ))}
                            </ol>
                        ) : (
                            <div className="flex items-center justify-center h-full text-muted-foreground">
                                <AlertCircle className="mr-2 h-4 w-4" />
                                No repositories in the queue
                            </div>
                        )}
        </div>
    );
}

function LoadingSkeleton() {
    return (
        <div className="container mx-auto p-4 h-[calc(100vh-2rem)] flex flex-col space-y-4">
            <Card className="h-1/4 min-h-[200px]">
                <CardHeader>
                    <Skeleton className="h-8 w-64" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full mt-2" />
                </CardContent>
            </Card>
            <Card className="h-3/4">
                <CardHeader>
                    <Skeleton className="h-8 w-64" />
                </CardHeader>
                <CardContent>
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full mt-2" />
                    <Skeleton className="h-4 w-full mt-2" />
                </CardContent>
            </Card>
        </div>
    );
}

